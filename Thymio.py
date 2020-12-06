# Communication with Thymio via serial port or tcp
# Author: Yves Piguet, EPFL

import threading

class Message:
    """Aseba message data.
    """

    # v5
    ID_BOOTLOADER_RESET = 0x8000
    ID_BOOTLOADER_READ_PAGE = 0x8001
    ID_BOOTLOADER_WRITE_PAGE = 0x8002
    ID_BOOTLOADER_PAGE_DATA_WRITE = 0x8003
    ID_BOOTLOADER_DESCRIPTION = 0x8004
    ID_BOOTLOADER_PAGE_DATA_READ = 0x8005
    ID_BOOTLOADER_ACK = 0x8006
    ID_DESCRIPTION = 0x9000
    ID_NAMED_VARIABLE_DESCRIPTION = 0x9001
    ID_LOCAL_EVENT_DESCRIPTION = 0x9002
    ID_NATIVE_FUNCTION_DESCRIPTION = 0x9003
    ID_VARIABLES = 0x9005
    ID_EXECUTION_STATE_CHANGED = 0x900a
    ID_NODE_PRESENT = 0x900c
    ID_GET_DESCRIPTION = 0xa000
    ID_SET_BYTECODE = 0xa001
    ID_RESET = 0xa002
    ID_RUN = 0xa003
    ID_PAUSE = 0xa004
    ID_STEP = 0xa005
    ID_STOP = 0xa006
    ID_GET_EXECUTION_STATE = 0xa007
    ID_BREAKPOINT_SET = 0xa008
    ID_BREAKPOINT_CLEAR = 0xa009
    ID_BREAKPOINT_CLEAR_ALL = 0xa00a
    ID_GET_VARIABLES = 0xa00b
    ID_SET_VARIABLES =  0xa00c
    ID_GET_NODE_DESCRIPTION = 0xa010
    ID_LIST_NODES = 0xa011
    # v6
    ID_GET_DEVICE_INFO = 0xa012
    ID_SET_DEVICE_INFO = 0xa013
    # v7
    ID_GET_CHANGED_VARIABLES = 0xa014
    # v8
    ID_GET_NODE_DESCRIPTION_FRAGMENT = 0xa015

    PROTOCOL_VERSION = 5

    def __init__(self, id, source_node, payload):
        self.id = id
        self.source_node = source_node
        self.payload = payload

    def get_uint16(self, offset):
        """Get an unsigned 16-bit integer in the payload.
        """
        return self.payload[offset] + 256 * self.payload[offset + 1], offset + 2

    def get_string(self, offset):
        """Get a string in the payload.
        """
        len = self.payload[offset]
        str = self.payload[offset + 1 : offset + 1 + len]
        return str.decode('utf-8'), offset + 1 + len

    @staticmethod
    def uint16_to_bytes(word):
        """Convert an unsigned 16-bit integer to bytes.
        """
        return bytes([word % 256, word // 256])

    @staticmethod
    def uint16array_to_bytes(a):
        """Convert an array of unsigned 16-bit integer to bytes.
        """
        bytes = b"";
        for word in a:
            bytes += Message.uint16_to_bytes(word)
        return bytes

    def decode(self):
        """Decode message properties from its payload.
        """
        if self.id == Message.ID_DESCRIPTION:
            self.node_name, offset = self.get_string(0)
            self.protocol_version, offset = self.get_uint16(offset)
            self.bytecode_size, offset = self.get_uint16(offset)
            self.stack_size, offset = self.get_uint16(offset)
            self.var_size, offset = self.get_uint16(offset)
            self.num_named_var, offset = self.get_uint16(offset)
            self.num_local_events, offset = self.get_uint16(offset)
            self.num_native_fun, offset = self.get_uint16(offset)
        elif self.id == Message.ID_NAMED_VARIABLE_DESCRIPTION:
            self.var_size, offset = self.get_uint16(0)
            self.var_name, offset = self.get_string(offset)
        elif self.id == Message.ID_LOCAL_EVENT_DESCRIPTION:
            self.event_name, offset = self.get_string(0)
            self.description, offset = self.get_string(offset)
        elif self.id == Message.ID_NATIVE_FUNCTION_DESCRIPTION:
            self.fun_name, offset = self.get_string(0)
            self.description, offset = self.get_string(offset)
            num_params, offset = self.get_uint16(offset)
            self.param_names = []
            self.param_sizes = []
            for i in range(num_params):
                size, offset = self.get_uint16(offset)
                name, offset = self.get_string(offset)
                self.param_names.append(name)
                self.param_sizes.append(size)
        elif self.id == Message.ID_VARIABLES:
            self.var_offset, offset = self.get_uint16(0)
            self.var_data = []
            for i in range(len(self.payload) // 2 - 1):
                word, offset = self.get_uint16(offset)
                self.var_data.append(word)
        elif self.id == Message.ID_NODE_PRESENT:
            self.version, offset = self.get_uint16(0)
        elif self.id == Message.ID_SET_BYTECODE:
            self.target_node_id, offset = self.get_uint16(0)
            self.bc_offset, offset = self.get_uint16(offset)
            val = []
            for i in range(4, len(self.payload), 2):
                instr, offset = get_uint16(offset)
                val.append(instr)
            self.bc = val
        elif (self.id == Message.ID_BREAKPOINT_CLEAR_ALL or
              self.id == Message.ID_RESET or
              self.id == Message.ID_RUN or
              self.id == Message.ID_PAUSE or
              self.id == Message.ID_STEP or
              self.id == Message.ID_STOP or
              self.id == Message.ID_GET_EXECUTION_STATE):
            self.target_node_id, offset = self.get_uint16(0)
        elif (self.id == Message.ID_BREAKPOINT_SET or
              self.id == Message.ID_BREAKPOINT_CLEAR):
            self.target_node_id, offset = self.get_uint16(0)
            self.pc, offset = self.get_uint16(offset)
        elif self.id == Message.ID_GET_VARIABLES:
            self.target_node_id, offset = self.get_uint16(0)
            self.var_offset, offset = self.get_uint16(offset)
            self.var_count, offset = self.get_uint16(offset)
        elif self.id == Message.ID_SET_VARIABLES:
            self.target_node_id, offset = self.get_uint16(0)
            self.var_offset, offset = self.get_uint16(offset)
            val = []
            for i in range(4, len(self.payload), 2):
                v, offset = get_uint16(offset)
                val.append(v)
            self.var_val = val
        elif self.id == Message.ID_LIST_NODES:
            self.version, offset = self.get_uint16(0)

    def serialize(self):
        """Serialize message to bytes.
        """
        return (self.uint16_to_bytes(len(self.payload)) +
                self.uint16_to_bytes(self.source_node) +
                self.uint16_to_bytes(self.id) +
                self.payload)

    @staticmethod
    def id_to_str(id):
        """Convert message id to its name string.
        """
        try:
            return {
                Message.ID_DESCRIPTION: "DESCRIPTION",
                Message.ID_NAMED_VARIABLE_DESCRIPTION: "ID_NAMED_VARIABLE_DESCRIPTION",
                Message.ID_LOCAL_EVENT_DESCRIPTION: "ID_LOCAL_EVENT_DESCRIPTION",
                Message.ID_NATIVE_FUNCTION_DESCRIPTION: "ID_NATIVE_FUNCTION_DESCRIPTION",
                Message.ID_VARIABLES: "ID_VARIABLES",
                Message.ID_EXECUTION_STATE_CHANGED: "ID_EXECUTION_STATE_CHANGED",
                Message.ID_NODE_PRESENT: "ID_NODE_PRESENT",
                Message.ID_GET_DESCRIPTION: "ID_GET_DESCRIPTION",
                Message.ID_SET_BYTECODE: "ID_SET_BYTECODE",
                Message.ID_RESET: "ID_RESET",
                Message.ID_RUN: "ID_RUN",
                Message.ID_PAUSE: "ID_PAUSE",
                Message.ID_STEP: "ID_STEP",
                Message.ID_STOP: "ID_STOP",
                Message.ID_GET_EXECUTION_STATE: "ID_GET_EXECUTION_STATE",
                Message.ID_BREAKPOINT_SET: "ID_BREAKPOINT_SET",
                Message.ID_BREAKPOINT_CLEAR: "ID_BREAKPOINT_CLEAR",
                Message.ID_BREAKPOINT_CLEAR_ALL: "ID_BREAKPOINT_CLEAR_ALL",
                Message.ID_GET_VARIABLES: "ID_GET_VARIABLES",
                Message.ID_SET_VARIABLES: "ID_SET_VARIABLES",
                Message.ID_GET_NODE_DESCRIPTION: "ID_GET_NODE_DESCRIPTION",
                Message.ID_LIST_NODES: "ID_LIST_NODES",
            }[id]
        except KeyError as error:
            return f"ID {id}"

    def __str__(self):
        str = f"Message id={self.id_to_str(self.id)} src={self.source_node}"
        if self.id == Message.ID_DESCRIPTION:
            str += f" name={self.node_name}"
            str += f" vers={self.protocol_version}"
            str += f" bc_size={self.bytecode_size}"
            str += f" stack_size={self.stack_size}"
            str += f" var_size={self.var_size}"
            str += f" #var={self.num_named_var}"
            str += f" #ev={self.num_local_events}"
            str += f" #nat={self.num_native_fun}"
        elif self.id == Message.ID_NAMED_VARIABLE_DESCRIPTION:
            str += f" name={self.var_name} size={self.var_size}"
        elif self.id == Message.ID_LOCAL_EVENT_DESCRIPTION:
            str += f" name={self.event_name} descr={self.description}"
        elif self.id == Message.ID_NATIVE_FUNCTION_DESCRIPTION:
            str += f" name={self.fun_name} descr={self.description} p=("
            for i in range(len(self.param_names)):
                str += f"{self.param_names[i]}[{self.param_sizes[i] if self.param_sizes[i] != 65535 else '?'}],"
            str += ")"
        elif self.id == Message.ID_VARIABLES:
            str += f" offset={self.var_offset} data=("
            for word in self.var_data:
                str += f"{word},"
            str += ")"
        elif self.id == Message.ID_NODE_PRESENT:
            str += f" version={self.version}"
        return str


class InputThread(threading.Thread):
    """Thread which reads messages asynchronously.
    """

    def __init__(self, io, handle_msg=None):
        threading.Thread.__init__(self)
        self.io = io
        self.handle_msg = handle_msg

    def read_uint16(self):
        """Read an unsigned 16-bit number.
        """
        b = self.io.read(2)
        return b[0] + 256 * b[1]

    def read_message(self):
        """Read a complete message.
        """
        try:
            payload_len = self.read_uint16()
            source_node = self.read_uint16()
            id = self.read_uint16()
            payload = self.io.read(payload_len)
        except:
            return None
        msg = Message(id, source_node, payload)
        return msg

    def run(self):
        """Input thread code.
        """
        while True:
            msg = self.read_message()
            if msg:
                msg.decode()
                if self.handle_msg:
                    self.handle_msg(msg)
            else:
                break


class RemoteNode:
    """Remote node description and state.
    """

    def __init__(self):
        self.node_id = None
        self.node_name = None
        self.var_total_size = 0
        self.var_offset = {}
        self.var_size = {}
        self.var_data = []

    def add_var(self, name, size):
        """Add the definition of a variable.
        """
        self.var_offset[name] = self.var_total_size
        self.var_size[name] = size
        self.var_total_size += size

    def reset_var_data(self):
        """Reset the variable data to 0.
        """
        self.var_data = [0 for i in range(self.var_total_size)]

    def get_var(self, name, index=0):
        """Get the value of a scalar variable or an item in an array variable.
        """
        return self.var_data[self.var_offset[name] + index]

    def get_var_array(self, name):
        """Get the value of an array variable.
        """
        offset = self.var_offset[name]
        return self.var_data[offset : offset + self.var_size[name]]

    def set_var(self, name, val, index=0):
        """Set the value of a scalar variable or an item in an array variable.
        """
        self.var_data[self.var_offset[name] + index] = val

    def set_var_array(self, name, val):
        """Set the value of an array variable.
        """
        offset = self.var_offset[name]
        self.var_data[offset : offset + len(val)] = val

    def set_var_data(self, offset, data):
        """Set values in the variable data array.
        """
        self.var_data[offset : offset + len(data)] = data


class Thymio:
    """Connection to a Thymio.
    """

    def __init__(self, io, node_id=1, refreshing_rate=None):
        self.terminating = False
        self.io = io
        self.node_id = node_id
        self.remote_node = RemoteNode()
        self.auto_handshake = False

        self.input_lock = threading.Lock()
        self.input_thread = InputThread(self.io,
                                        lambda msg: self.handle_message(msg))
        self.input_thread.start()

        self.output_lock = threading.Lock()
        self.refreshing_timeout = None
        self.refreshing_trigger = threading.Event()  # initially wait() blocks
        def do_refresh():
            while not self.terminating:
                self.refreshing_trigger.wait(self.refreshing_timeout)
                self.refreshing_trigger.clear()
                self.get_variables()
        self.refresh_thread = threading.Thread(target=do_refresh)
        self.refresh_thread.start()
        if refreshing_rate is not None:
            self.set_refreshing_rate(refreshing_rate)

    def close(self):
        """Close connection.
        """
        self.io.close()

    def __del__(self):
        self.terminating = True
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @staticmethod
    def serial_default_port():
        """Get the name of the default Thymio serial port for the current platform.
        """
        import sys
        import os
        if sys.platform == "linux":
            return [
                "/dev/" + filename
                for filename in os.listdir("/dev")
                if filename.startswith("ttyACM")
            ][0]
        if sys.platform == "darwin":
            return [
                "/dev/" + filename
                for filename in os.listdir("/dev")
                if filename.startswith("cu.usb")
            ][0]
        if sys.platform == "win32":
            return "COM8"

    @staticmethod
    def serial(port=None, node_id=1, refreshing_rate=None):
        """Create Thymio object with a serial connection.
        """
        import serial  # pip3 install pyserial
        if port is None:
            port = Thymio.serial_default_port()
        th = Thymio(serial.Serial(port), node_id, refreshing_rate)
        th.handshake()
        return th

    @staticmethod
    def tcp(host="127.0.0.1", port=3000, node_id=1, refreshing_rate=None):
        """Create Thymio object with a TCP connection.
        """
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        th = Thymio(s, node_id, refreshing_rate)
        th.handshake()
        return th

    @staticmethod
    def null(node_id=1, refreshing_rate=None):
        """Create Thymio object without connection.
        """
        import io
        class NullIO(io.RawIOBase):
            def read(self, n):
                return None
            def write(self, b):
                pass
        return Thymio(NullIO(), node_id)

    def handshake(self):
        self.auto_handshake = True
        self.list_nodes()

    def set_refreshing_rate(self, rate):
        """Change the auto-refresh rate to update variables.
        """
        self.refreshing_timeout = rate
        if rate is not None:
            # refresh now
            self.refreshing_trigger.set()

    def handle_message(self, msg):
        """Handle an input message.
        """
        if msg.id == Message.ID_NODE_PRESENT:
            with self.input_lock:
                self.remote_node.node_id = msg.source_node
            if self.auto_handshake:
                self.get_node_description()
        elif msg.id == Message.ID_DESCRIPTION:
            with self.input_lock:
                self.remote_node.name = msg.node_name
        elif msg.id == Message.ID_NAMED_VARIABLE_DESCRIPTION:
            with self.input_lock:
                self.remote_node.add_var(msg.var_name, msg.var_size)
        elif msg.id == Message.ID_VARIABLES:
            with self.input_lock:
                self.remote_node.set_var_data(msg.var_offset, msg.var_data)
        elif msg.id == Message.ID_NATIVE_FUNCTION_DESCRIPTION:
            pass  # ignore
        elif msg.id == Message.ID_LOCAL_EVENT_DESCRIPTION:
            pass  # ignore
        else:
            print(msg)

    def send(self, msg):
        """Send a message.
        """
        with self.output_lock:
            self.io.write(msg.serialize())

    def get_target_node_id(self):
        """Get target node ID.
        """
        with self.input_lock:
            return self.remote_node.node_id

    def get_target_node_var_total_size(self):
        """Get the total size of variables.
        """
        with self.input_lock:
            return self.remote_node.var_total_size

    def list_nodes(self):
        """Send a LIST_NODES message.
        """
        payload = Message.uint16array_to_bytes([Message.PROTOCOL_VERSION])
        msg = Message(Message.ID_LIST_NODES, self.node_id, payload)
        self.send(msg)

    def get_node_description(self, target_node_id=None):
        """Send a GET_NODE_DESCRIPTION message.
        """
        payload = Message.uint16array_to_bytes([
            self.get_target_node_id() if target_node_id is None else target_node_id,
            Message.PROTOCOL_VERSION
        ])
        msg = Message(Message.ID_GET_NODE_DESCRIPTION, self.node_id, payload)
        self.send(msg)

    def get_variables(self, chunk_offset=0, chunk_length=None, target_node_id=None):
        """Send a GET_VARIABLES message.
        """
        if target_node_id is None:
            target_node_id = self.get_target_node_id()
        if target_node_id is not None:
            payload = Message.uint16array_to_bytes([
                self.get_target_node_id() if target_node_id is None else target_node_id,
                chunk_offset,
                self.get_target_node_var_total_size() if chunk_length is None else chunk_length
            ])
            msg = Message(Message.ID_GET_VARIABLES, self.node_id, payload)
            self.send(msg)

    def set_variables(self, chunk_offset, chunk, target_node_id=None):
        """Send a SET_VARIABLES message.
        """
        payload = Message.uint16array_to_bytes([
            self.get_target_node_id() if target_node_id is None else target_node_id,
            chunk_offset
        ] + chunk)
        msg = Message(Message.ID_SET_VARIABLES, self.node_id, payload)
        self.send(msg)

    def variable_description(self):
        """Get an array with the description of all variables, with fields "name", "offset" and "size".
        """
        return [
            {
                "name": key,
                "offset": self.remote_node.var_offset[key],
                "size": self.remote_node.var_size[key]
            }
            for key in self.remote_node.var_offset.keys()
        ]

    def get_var(self, name, index=0):
        """Get the value of a scalar variable from the local copy.
        """
        with self.input_lock:
            return self.remote_node.get_var(name, index)

    def get_var_array(self, name):
        """Get the value of an array variable from the local copy.
        """
        with self.input_lock:
            return self.remote_node.get_var_array(name)

    def set_var(self, name, val, index=0):
        """Set the value of a scalar variable in the local copy and send it.
        """
        with self.input_lock:
            self.remote_node.set_var(name, val, index)
        self.set_variables(self.remote_node.var_offset[name] + index,
                           [val])

    def set_var_array(self, name, val):
        """Set the value of an array variable in the local copy and send it.
        """
        with self.input_lock:
            self.remote_node.set_var_array(name, val)
        self.set_variables(self.remote_node.var_offset[name], val)

    def __getitem__(self, key):
        val = self.get_var_array(key)
        return val if len(val) != 1 else val[0]

    def __setitem__(self, key, val):
        if isinstance(val, list):
            self.set_var_array(key, val)
        else:
            self.set_var(key, val)


if __name__ == "__main__":
    import time
    with Thymio.serial(refreshing_rate=0.1) as th:
        while True:
            try:
                print(th["prox.horizontal"])
            except KeyError:
                pass
            time.sleep(0.2)
