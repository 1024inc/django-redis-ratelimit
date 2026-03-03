# DEPRECATED !!!!

Functionality of this repository was replaced by [limits](https://pypi.org/project/limits/)
in this [commit](https://github.com/1024inc/beyondpricing/commit/6d846fa00036933d13543480f0fa8ce22952c198).

# django-redis-ratelimit

Forked version of https://github.com/romantomjak/django-redis-ratelimit with
resilience to Redis connection errors, so that Redis is not in the critical
path of your endpoints.


## Test
Run all tests:

    docker-compose run test

Run an individual test:

    docker-compose run test tests.tests.RateLimitTests

## Usage
See instructions at https://github.com/romantomjak/django-redis-ratelimit

### Django Settings
- `REDIS_RATELIMIT_DB_URL`: Redis URL (defaults to `redis://localhost:6379/0`)
- `REDIS_RATELIMIT_DB_TIMEOUT`: Timeout to connect and run commands in seconds (defaults to `0.1`)
