import ujson

from funnel_backend.message_protocol import MessageBase, Subscription, ResponseMessage, ErrorMessage, Update, WSMsgType, ParamsMessage


class MessageConverter:
    msg_mappings = {
        WSMsgType.subscribe.value: Subscription,
        WSMsgType.updateValue.value: Update,
        WSMsgType.snapshot.value: ParamsMessage,
        WSMsgType.update.value: ParamsMessage
    }

    @staticmethod
    def serialise_message(msg_obj: MessageBase) -> bytes:
        msg_dict = msg_obj.get_as_dict()
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


