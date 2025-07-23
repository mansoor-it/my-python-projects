# ملف main.py
from logger_setup_main import setup_logger

# إعداد logger
logger = setup_logger()

def main():
    logger.info("Application started")
    try:
        # تنفيذ بعض العمليات
        logger.debug("Debugging information")
    except Exception as e:
        logger.error("An error occurred: %s", e)
    finally:
        logger.info("Application ended")

if __name__ == "__main__":
    main()