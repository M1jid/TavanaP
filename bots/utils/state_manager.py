class StateManager:
    def __init__(self):
        self.user_states = {}

    def get_state(self, user_id):
        return self.user_states.get(user_id)

    def update_state(self, user_id, state, data=None):
        if user_id not in self.user_states:
            self.user_states[user_id] = {"state": state, "data": data or {}}
        else:
            self.user_states[user_id]["state"] = state
            if data is not None:
                self.user_states[user_id]["data"] = data

    def clear_state(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]