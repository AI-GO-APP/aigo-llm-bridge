class BridgeError(Exception):
    """Only trusted, content-free diagnostics may be constructed here."""
    def __init__(self, status, category, message, parameter=None):
        super().__init__(category)
        self.status, self.category, self.message, self.parameter = status, category, message, parameter

    def body(self):
        metadata = {"error_type": self.category}
        if self.parameter:
            metadata["parameter"] = self.parameter
        return {"error": {"code": self.status, "message": self.message, "metadata": metadata}}
