#!/usr/bin/env python3
"""FunctionRegistry basic tests"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.function_registry import register_function, get_registry

# Dummy functions -----------------------------------------------------------
@register_function(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@register_function(name="echo")
def echo_text(text: str) -> str:
    return text

def test_registry_schema_generation():
    registry = get_registry()
    schemas = registry.get_schema_list()
    names = [s["name"] for s in schemas]
    assert "add" in names
    assert "echo" in names
    # parameters required keys
    add_schema = next(s for s in schemas if s["name"] == "add")
    assert set(add_schema["parameters"]["required"]) == {"a", "b"}


def test_callable_execution():
    registry = get_registry()
    add_fn = registry.get_callable("add")
    echo_fn = registry.get_callable("echo")
    assert add_fn(2, 3) == 5
    assert echo_fn("hello") == "hello"

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__])) 