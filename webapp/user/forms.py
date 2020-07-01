from flask_wtf import FlaskForm

class SpecsForm(FlaskForm):
    pass
    # name = phone.name
    # os = phone.os
    # num_of_sims = phone.num_of_sims

    # name = db.Column(db.String, nullable=True, unique=True)
    # photos = db.Column(db.String, nullable=True)
    # os = db.Column(db.String, nullable=True)
    # num_of_sims = db.Column(db.String, nullable=True)
    # sim_type = db.Column(db.String, nullable=True)
    # weight = db.Column(db.Float, nullable=True)
    # size = db.Column(db.String,
    #                  nullable=True)  # наверное лучше указать размер строкой вида "160, 80, 20", а потом её сплитить
    # # url = db.Column(db.String, nullable=True, unique=True)
    #
    # # Экран
    # screen_type = db.Column(db.String, nullable=True)
    # screen_size = db.Column(db.String, nullable=True)
    # resolution = db.Column(db.String, nullable=True)
    # ppi = db.Column(db.String, nullable=True)
    # ips = db.Column(db.String, nullable=True)
    #
    # # Мультимедиа
    # main_cam_resolution = db.Column(db.String, nullable=True)
    # selfie_cam_resolution = db.Column(db.String, nullable=True)
    # aperture = db.Column(db.String, nullable=True)
    # selfie_aperture = db.Column(db.String, nullable=True)
    # flash = db.Column(db.String, nullable=True)
    # max_video_resolution = db.Column(db.String, nullable=True)
    # selfie_cam = db.Column(db.String, nullable=True)
    # audio_formats = db.Column(db.String, nullable=True)
    # headphones_jack = db.Column(db.String, nullable=True)
    #
    # # Связь
    # types = db.Column(db.String, nullable=True)
    # bluetooth_version = db.Column(db.String, nullable=True)
    #
    # # Батарея
    # battery_capacity = db.Column(db.String, nullable=True)
    # charge_connector = db.Column(db.String, nullable=True)
    # quick_charge = db.Column(db.String, nullable=True)
    #
    # # Память и процессор
    # processor = db.Column(db.String, nullable=True)
    # processor_cores = db.Column(db.String, nullable=True)
    # gpu = db.Column(db.String, nullable=True)
    # ram = db.Column(db.String, nullable=True)
    # sdcard_slot = db.Column(db.String, nullable=True)