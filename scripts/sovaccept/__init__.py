"""Reading and checking of the owner acceptance register.

The package exists to make one rule mechanical: the owner gate is acceptance of a
finished result, and a transition may wait on the owner only for a reason
``contracts/acceptance-policy.json`` names. Everything here reads; nothing here
decides. An owner action is taken by the owner and recorded, never inferred.
"""
