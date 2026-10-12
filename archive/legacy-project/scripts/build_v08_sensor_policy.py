"""Build a diagnostic candidate; never bypass original size comparisons."""
from build_v07_sensor_policy import build, ROOT

if __name__ == '__main__':
    build(preserve_size_checks=True, destination=ROOT/'patches/front-v0.8-policy')
