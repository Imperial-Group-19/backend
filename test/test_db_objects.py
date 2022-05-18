# {
#             "productName": "cpp-course",
#             "title": "cc",
#             "description": "casd",
#             "storeAddress": "0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
#             "price": 50000000000000000,
#             "features": ["feature 1"],
#             "productType": 0
#         }

from funnel_backend.db_objects import Product


def test_1():
    first_product = Product(
        productName="cpp-course",
        storeAddress="0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
        title="cc",
        description="casd",
        price=50000000000000000,
        features=["feature 1"],
        productType=0
    )

    second_product = Product(
        productName="cpp-course",
        storeAddress="0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
        title="cc",
        description="casd",
        price=50000000000000000,
        features=["feature 1"],
        productType=0
    )

    a = {first_product: first_product, second_product: second_product}
    assert(first_product in a)
    assert(second_product in a)


def test_2():
    first_product = Product(
        productName="cpp-course",
        storeAddress="0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
        title="cc",
        description="casd",
        price=50000000000000000,
        features="feature 1",
        productType=0
    )

    assert(first_product.features == ["feature 1"])

    second_product = Product(
        productName="cpp-course",
        storeAddress="0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
        title="cc",
        description="casd",
        price=50000000000000000,
        features=["feature 1"],
        productType=0
    )

    assert(second_product.features == ["feature 1"])

    third_product = Product(
        productName="cpp-course",
        storeAddress="0x02b7433EA4f93554856aa657Da1494B2Bf645EF0",
        title="cc",
        description="casd",
        price=50000000000000000,
        features=[["feature 1"]],
        productType=0
    )

    assert(third_product.features == ["feature 1"])
