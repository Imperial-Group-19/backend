import ujson
from message_protocol import MessageBase, Subscription, ResponseMessage, ErrorMessage


class MsgConverter:
    msg_mappings = {
        Subscription.method: Subscription
    }

    @staticmethod
    def serialise_message(msg_obj: MessageBase) -> bytes:
        msg_dict = msg_obj.get_as_dict()
        print(msg_dict)
        return ujson.dumps(obj=msg_dict, escape_forward_slashes=False).encode("utf-8")

    def deserialise_message(self, data: bytes) -> MessageBase:
        msg_dict = ujson.loads(data.decode("utf-8"))
        msg_method = msg_dict.get("method", None)
        if msg_method in self.msg_mappings:
            msg_cls = self.msg_mappings.get(msg_method, None)
            if msg_cls is not None:
                return msg_cls(**msg_dict)

        msg_result = msg_dict.get("result", None)
        if msg_result is not None:
            return ResponseMessage(**msg_dict)

        msg_result = msg_dict.get("error", None)
        if msg_result is not None:
            return ErrorMessage(**msg_dict)

        # for now throw exception
        raise Exception(f"Incorrectly formatted or unrecognised msg: {data}")


if __name__ == "__main__":
    from message_protocol import ErrorType
    msg_converter = MsgConverter()

    def test_1():
        subscribe = Subscription(id=2, jsonrpc="2.0", method="subscribe", params=["kamil"])
        bytes_msg = msg_converter.serialise_message(subscribe)
        msg_obj = msg_converter.deserialise_message(bytes_msg)
        assert(subscribe == msg_obj)

    def test_2():
        subscribe_response = ResponseMessage(id=2, jsonrpc="2.0", result=True)
        bytes_msg = msg_converter.serialise_message(subscribe_response)
        msg_obj = msg_converter.deserialise_message(bytes_msg)
        assert(subscribe_response == msg_obj)

    def test_3():
        subscribe_error = ErrorMessage(id=2, jsonrpc="2.0", error=ErrorType(code=3, message="error"))
        bytes_msg = msg_converter.serialise_message(subscribe_error)
        msg_obj = msg_converter.deserialise_message(bytes_msg)
        assert(subscribe_error == msg_obj)

    test_1()
    test_2()
    test_3()
