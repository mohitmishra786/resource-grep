import redis
import logging
import time
import json
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import subprocess
import hashlib
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class CrawlerCoordinator:
    """Coordinates distributed crawlers using Redis"""
    
    def __init__(self, redis_host='redis', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port)
        self.running = True
        self.worker_count = int(os.environ.get('CRAWLER_WORKERS', 3))
        self.workers = {}
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Gracefully shut down workers"""
        logger.info("Shutting down crawler coordinator")
        self.running = False
        
        # Stop all workers
        for worker_id, process in self.workers.items():
            logger.info(f"Stopping worker {worker_id}")
            process.terminate()
        
        sys.exit(0)
    
    def ensure_worker_count(self):
        """Ensure desired number of workers are running"""
        # Check currently running workers
        running_workers = {}
        for worker_id, process in self.workers.items():
            if process.poll() is None:  # Process is still running
                running_workers[worker_id] = process
            else:
                logger.info(f"Worker {worker_id} exited with code {process.returncode}")
        
        # Update workers dict
        self.workers = running_workers
        
        # Start new workers if needed
        while len(self.workers) < self.worker_count:
            worker_id = f"worker_{random.randint(1000, 9999)}"
            logger.info(f"Starting new crawler worker {worker_id}")
            
            # Start crawler process
            cmd = [
                'scrapy', 'crawl', 'distributed_resource_spider',
                '-a', f'worker_id={worker_id}'
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.workers[worker_id] = process
    
    def distribute_urls(self):
        """Distribute pending URLs to worker-specific queues"""
        # Get pending URLs
        pending_urls = self.redis.lrange('crawler:pending_urls', 0, 100)
        
        if not pending_urls:
            return
        
        # Get active worker IDs
        worker_ids = list(self.workers.keys())
        if not worker_ids:
            return
        
        # Distribute URLs to workers
        for url_bytes in pending_urls:
            url = url_bytes.decode('utf-8')
            # Select worker based on URL hash for consistent assignment
            url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
            worker_idx = url_hash % len(worker_ids)
            worker_id = worker_ids[worker_idx]
            
            # Add to worker's queue
            worker_queue = f'crawler:pending_urls:{worker_id}'
            self.redis.rpush(worker_queue, url)
            
            # Remove from main queue
            self.redis.lrem('crawler:pending_urls', 1, url_bytes)
    
    def seed_urls(self):
        """Seed initial URLs if the queue is empty"""
        pending_count = self.redis.llen('crawler:pending_urls')
        seen_count = self.redis.scard('crawler:seen_urls')
        
        if pending_count == 0 and seen_count == 0:
            logger.info("Seeding initial URLs")
            
            # Import spider to get default URLs
            try:
                from crawler.resource_crawler.spiders.distributed_spider import DistributedResourceSpider
                
                # Add default URLs to queue
                for url in DistributedResourceSpider.default_start_urls:
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    if not self.redis.sismember('crawler:seen_urls', url_hash):
                        self.redis.rpush('crawler:pending_urls', url)
                        self.redis.sadd('crawler:seen_urls', url_hash)
                        
                logger.info(f"Seeded {len(DistributedResourceSpider.default_start_urls)} URLs")
            except ImportError:
                logger.error("Could not import DistributedResourceSpider to seed URLs")
    
    def report_stats(self):
        """Report crawler statistics"""
        visited = self.redis.scard('crawler:visited_urls')
        pending = self.redis.llen('crawler:pending_urls')
        seen = self.redis.scard('crawler:seen_urls')
        
        logger.info(f"Crawler stats: visited={visited}, pending={pending}, seen={seen}, workers={len(self.workers)}")
    
    def run(self):
        """Main coordinator loop"""
        logger.info("Starting crawler coordinator")
        
        # Seed initial URLs
        self.seed_urls()
        
        try:
            while self.running:
                # Ensure worker count
                self.ensure_worker_count()
                
                # Distribute URLs
                self.distribute_urls()
                
                # Report stats
                self.report_stats()
                
                # Sleep
                time.sleep(5)
        except KeyboardInterrupt:
            self.shutdown(None, None)
        except Exception as e:
            logger.error(f"Coordinator error: {e}")
            self.shutdown(None, None)

if __name__ == "__main__":
    # Get Redis connection details from environment
    redis_host = os.environ.get('REDIS_HOST', 'redis')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    
    coordinator = CrawlerCoordinator(redis_host, redis_port)
    coordinator.run() 