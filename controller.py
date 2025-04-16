import uuid
import asyncio


class Request:
    def __init__(self, id: uuid.UUID, op: int, name: str):
        self.id: uuid.UUID = id
        self.op: int = op
        self.name: str = name
        self.fut: asyncio.Future = None


class Controller:
    def __init__(self):
        self.edit_mode = False
        self.requests = {}

    def editMode(self) -> bool:
        return self.edit_mode

    def turnOnEdit(self):
        self.edit_mode = True

    def turnOffEdit(self):
        self.edit_mode = False

    def acceptRequest(self, id: uuid.UUID):
        self.resolveRequest(True, id)
        print("accept", id)

    def rejectRequest(self, id: uuid.UUID):
        self.resolveRequest(False, id)
        print("reject", id)

    def resolveRequest(self, result: bool, id: uuid.UUID):
        if id in self.requests:
            self.requests[id].fut.set_result(result)
            self.requests.pop(id)
        else:
            print("There is no such request with id:", id)

    async def handleRequest(self, req: Request):
        from frontend import askRequest

        self.requests[req.id] = req
        await askRequest(req)


controller = Controller()
