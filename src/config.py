
# Redis for sharing state between all non-monkeyrunner processes
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Monkeyrunner device client / server communication (no redis installation
# in jython :(
DEVICE_HOST = '127.0.0.1'
DEVICE_PORT = 5005

TFNET_CONFIG = {
    'model': 'cfg/tiny-yolo.cfg',
    'load': 'dfbin/tiny-yolo.weights',
    'gpu': 0.7,
    'threshold': 0.1
}

VYSOR_WINDOW_NAME = 'Kim'  # 'Vysor'
