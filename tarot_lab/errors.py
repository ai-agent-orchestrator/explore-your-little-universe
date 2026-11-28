class LumiError(Exception):
    code = 'service_unavailable'
    status_code = 503

class IdempotencyConflict(LumiError):
    code = 'idempotency_conflict'
    status_code = 409

class NotFound(LumiError):
    code = 'not_found'
    status_code = 404

class RunInProgress(LumiError):
    code = 'run_in_progress'
    status_code = 409

class ProfileMismatch(LumiError):
    code = 'profile_mismatch'

class GraphUnavailable(LumiError):
    code = 'graph_unavailable'

class VectorUnavailable(LumiError):
    code = 'vector_unavailable'

class LLMNotConfigured(LumiError):
    code = 'llm_not_configured'
