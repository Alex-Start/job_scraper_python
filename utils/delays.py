import random, time

# -----------------------------------
# HUMAN-LIKE DELAYS
# -----------------------------------
def human_delay(a=2, b=5):
    """Random sleep to look less like a bot"""
    time.sleep(random.uniform(a, b))