# encoding: utf-8

from pkg_resources import resource_filename



def get_dotted_object(target):
    """This helper function loads an object identified by a dotted-notation string.
    
    For example:
    
        # Load class Foo from example.objects
        get_dotted_object('example.objects:Foo')
    """
    parts, target = target.split(':') if ':' in target else (target, None)
    module = __import__(parts)
    
    for part in parts.split('.')[1:] + ([target] if target else []):
        module = getattr(module, part)
    
    return module