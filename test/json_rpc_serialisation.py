from funnel_backend.message_protocol import ErrorType, Subscription, ResponseMessage, ErrorMessage, Update, DBType, \
    WSMsgType
from funnel_backend.message_conversion import MessageConverter
from funnel_backend.db_objects import Product


msg_converter = MessageConverter()


def test_1():
    subscribe = Subscription(id=2, jsonrpc="2.0", method="subscribe", params=["kamil"])
    bytes_msg = msg_converter.serialise_message(subscribe)
    msg_obj = msg_converter.deserialise_message(bytes_msg)
    assert (subscribe == msg_obj)


def test_2():
    subscribe_response = ResponseMessage(id=2, jsonrpc="2.0", result=True)
    bytes_msg = msg_converter.serialise_message(subscribe_response)
    msg_obj = msg_converter.deserialise_message(bytes_msg)
    assert (subscribe_response == msg_obj)


def test_3():
    subscribe_error = ErrorMessage(id=2, jsonrpc="2.0", error=ErrorType(code=3, message="error"))
    bytes_msg = msg_converter.serialise_message(subscribe_error)
    msg_obj = msg_converter.deserialise_message(bytes_msg)
    assert (subscribe_error == msg_obj)


def test_4():
    new_product = Product(
        productName="C#",
        storeAddress="hey",
        title="C# course",
        description="Try out our newest course in C# and impress your interviewers.",
        price=45000,
        features=[
            "Full algorithms course in C#"
        ],
        productType=1
    )
    response = Update(id=10, jsonrpc="2.0", method=WSMsgType.updateValue.value,
                      params=[DBType.products.value, new_product.__dict__])
    bytes_msg = msg_converter.serialise_message(response)
    msg_obj = msg_converter.deserialise_message(bytes_msg)
    assert (response == msg_obj)
