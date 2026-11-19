import restate
from sv_agent.main import service as sv_agent
from sv_input.main import service as sv_input
from sv_vector_db.main import service as sv_vector_db
from vo_user.main import virtual_object as vo_add_request

app = restate.app(services=[sv_agent, sv_input, sv_vector_db, vo_add_request])
