from __future__ import annotations


class Memory:
    memory = {
        'fact': None,
        'plan': None,
        'action': None,
        'product_specs': None,
    }

    @classmethod
    def set_memory(cls, key, value):
        cls.memory[key] = value

    @classmethod
    def get_memory(cls, key):
        return cls.memory.get(key)

    @classmethod
    def clear_memory(cls):
        cls.memory = {
            'fact': None,
            'plan': None,
            'action': None,
            'product_specs': None,
        }
