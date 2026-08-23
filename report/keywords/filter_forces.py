from keywords.routing_rules import should_block
from keywords.routing_rules import must_not_block
from keywords.routing_rules import must_not_country_block


forces = {
    # Force 1 - ارتش
    1: {                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        "must": [
            ["ارتش"],

            []
        ],
        "should": [
            should_block,

           ["ارتش ایران","ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block,
            
            []
        ]
    },

    # Force 2 - نیروی زمینی ارتش
    2: {
        "must": [
            ["نیروی زمینی"],

            ["نیرو زمینی"],

            []
        ],
        "should": [
            should_block,

            should_block,

            ["نیروی زمینی ارتش ایران","نیروی زمینی ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block + ["نیروی زمینی سپاه","نیروی زمینی شاهنشاهی"],

            must_not_country_block + ["نیرو زمینی سپاه","نیرو زمینی شاهنشاهی"],

            []
        ]
    },

    # Force 3 - نیروی هوایی ارتش
    3: {
        "must": [
            ["نیروی هوایی"],

            ["نیرو هوایی"],

            []
        ],
        "should": [
            should_block,

            should_block,

            ["نیروی هوایی ارتش ایران","نیروی هوایی ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block + ["نیروی هوایی شاهنشاهی"],

            must_not_country_block + ["نیرو هوایی شاهنشاهی"],

            []
        ]
    },

    # Force 4 - نیروی دریایی ارتش
    4: {
        "must": [
            ["نیروی دریایی"],

            ["نیرو دریایی"],

            []
        ],
        "should": [
            should_block,

            should_block,

            ["نیروی دریایی ارتش ایران","نیروی دریایی ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block + ["نیروی دریایی شاهنشاهی","نیروی دریایی سپاه"],

            must_not_country_block + ["نیرو دریایی شاهنشاهی","نیرو دریایی سپاه"],

            []
        ]
    },

    # Force 5 - نیروی پدافند هوایی ارتش
    5: {
        "must": [
            ["نیروی پدافند"],

            ["نیرو پدافند"],

            []
        ],
        "should": [
            should_block,

            should_block,

            ["نیروی پدافند ارتش ایران","نیروی پدافند هوایی ارتش ایران","نیروی پدافند ارتش جمهوری اسلامی","نیروی پدافند هوایی ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block,

            must_not_country_block,

            []
        ]
    },

    # Force 6 - عقیدتی سیاسی
    6: {
        "must": [
            ["عقیدتی سیاسی"],

            []
        ],
        "should": [
            should_block,

            ["عقیدتی سیاسی ارتش ایران","عقیدتی سیاسی ارتش جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block,

            []
        ]
    },

    # Force 7 - سپاه
    7: {                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        "must": [
            ["سپاه"]
        ],
        "should": [
            []
        ],
        "must_not": [
            []
        ]
    },

    # Force 8 -  نیرو زمینی سپاه
    8: {
        "must": [
            []
        ],
        "should": [
            ["نیروی زمینی سپاه","نیرو زمینی سپاه"]
        ],
        "must_not": [
            []
        ]
    },

    # Force 9 - نیروی هوافضای سپاه
    9: {
        "must": [
            []
        ],
        "should": [
            ["نیروی هوافضای سپاه","نیرو هوافضای سپاه","نیروی هوافضا سپاه","نیرو هوافضا سپاه"]
        ],
        "must_not": [
            []
        ]
    },

    # Force 10 - نیروی دریایی سپاه
    10: {
        "must": [
            []
        ],
        "should": [
            ["نیروی دریایی سپاه","نیرو دریایی سپاه"]
        ],
        "must_not": [
            []
        ]
    },

    # Force 11 - نیروی قدس سپاه
    11: {
        "must": [
            []
        ],
        "should": [
            ["نیروی قدس سپاه","نیرو قدس سپاه"]
        ],
        "must_not": [
            []
        ]
    },

    # Force 12 - سازمان بسیج
    12: {
        "must": [
            ["بسیج"]
        ],
        "should": [
            []
        ],
        "must_not": [
            must_not_block
        ]
    },

    # Force 13 - وزارت دفاع
    13: {
        "must": [
            ["وزارت دفاع"],

            []
        ],
        "should": [
            should_block,

            ["وزارت دفاع ایران","وزارت دفاع و پشتیبانی نیروهای مسلح ایران","وزارت دفاع جمهوری اسلامی","وزارت دفاع و پشتیبانی نیروهای مسلح جمهوری اسلامی"]
        ],
        "must_not": [
            must_not_country_block,

            []
        ]
    }
}