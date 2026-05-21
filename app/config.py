import os

class Config:
    """Base config share across environments"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///blog.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-in-production")

    # MEdia upload config
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # Flask request ceiling
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024 # 5 MB per file limit enforced in media blueprint
    USER_STORAGE_QUOTA = 500 * 1024 * 1024 # 500MB storage max per user

    # Cloud carousel
    # Use any absolute path (ie. from uploads) or public URL
    # Empty disables the feature
    CAROUSEL_IMAGES = ["https://static.wixstatic.com/media/982b4a_b1043398e8af44e4b718d9a2f19443a6~mv2.jpg/v1/fill/w_407,h_198,al_c,q_80,usm_0.66_1.00_0.01/982b4a_b1043398e8af44e4b718d9a2f19443a6~mv2.jpg",
                       "https://static.wixstatic.com/media/982b4a_fcdeee571f544c0abcc99f512e9458e8~mv2_d_2048_1536_s_2.jpg/v1/fill/w_407,h_305,al_c,q_80,usm_0.66_1.00_0.01/982b4a_fcdeee571f544c0abcc99f512e9458e8~mv2_d_2048_1536_s_2.jpg",
                       "https://static.wixstatic.com/media/982b4a_118cf7bcc3374237b6df0b9d77b782ba~mv2_d_4288_2848_s_4_2.jpg/v1/fill/w_407,h_270,al_c,q_80,usm_0.66_1.00_0.01/982b4a_118cf7bcc3374237b6df0b9d77b782ba~mv2_d_4288_2848_s_4_2.jpg",
                       "https://static.wixstatic.com/media/982b4a_26bb65d308ca4a2aad39563ee67ea287~mv2.jpg/v1/fill/w_407,h_325,al_c,q_80,usm_0.66_1.00_0.01/982b4a_26bb65d308ca4a2aad39563ee67ea287~mv2.jpg",
                       "https://static.wixstatic.com/media/982b4a_f0ff80f6fd5a47d388533306ad539184~mv2_d_4896_2760_s_4_2.jpg/v1/fill/w_407,h_229,al_c,q_80,usm_0.66_1.00_0.01/982b4a_f0ff80f6fd5a47d388533306ad539184~mv2_d_4896_2760_s_4_2.jpg"]

    # Main config
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = os.getenv("MAIL_PORT", 587)
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@blog.local")
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", False)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    MAIL_SUPPRESSED_SEND = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MAIL_SUPPRESS_SEND = True
    WTF_CSRF_ENABLED = False # Disable csrf in tests

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
