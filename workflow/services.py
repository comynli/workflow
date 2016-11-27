import datetime
import json
from .models import db
from .models import Schema, State, Transform, Field, Workflow, Data
from .struct import Digraph, Vertex, Edge
from sqlalchemy import or_


class SchemaService:
    def __init__(self, schema):
        self.schema = schema

    @classmethod
    def create(cls, name):
        schema = Schema(name=name)
        db.session.add(schema)
        try:
            db.session.commit()
            return SchemaService(schema)
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def get(cls, name):
        schema = Schema.query.filter(Schema.name == name).first()
        return SchemaService(schema)

    @classmethod
    def list(cls, page, size):
        pass

    def add_state(self, name, type):
        if not self.schema.editable:
            raise RuntimeError()
        # TODO

    def add_transform(self, perv, next):
        pass

    def add_field(self, state, name, type, required=True, desc=None):
        pass

    def copy(self, name):
        schema = Schema(name)
        states = []
        transforms = []
        for s in State.query.filter(State.schema_id == self.schema.id).all():
            fields = [Field(name=x.name, type=x.type, required=x.required, desc=x.desc) for x in s.fields]
            states.append(State(name=s.name, type=s.type, schema=schema, fileds=fields))
        # TODO process transform
        db.session.add(schema)
        for state in states:
            db.session.add(state)
        for transform in transforms:
            db.session.add(transform)
        try:
            db.session.commit()
            return SchemaService(schema)
        except Exception as e:
            db.session.rollback()
            raise e

    def validate(self) -> bool:
        g = Digraph()
        states = State.query.filter(State.schema_id == self.schema.id).all()
        for state in states:
            g.add_vertex(Vertex(state))
        state_ids = [x.id for x in states]
        transforms = Transform.query.filter(or_(Transform.prev.in_(state_ids), Transform.next.in_(state_ids))).all()
        for transform in transforms:
            g.add_edge(Edge(transform))
        if g.has_isolated_vertex():
            return False
        start_nodes = g.find_start()
        if len(start_nodes) != 1:
            return False
        if start_nodes[0].value.type != State.S:
            return False
        # TODO process END node
        if g.has_ring():
            return False
        return True

    def publish(self):
        if not self.validate():
            raise RuntimeError()
        self.schema.editable = False
        self.schema.active = True
        db.session.add(self.schema)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def offline(self):
        self.schema.active = False
        db.session.add(self.schema)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


class EngineService:
    def __init__(self, workflow):
        self.workflow = workflow

    @classmethod
    def validate(cls, state, data):
        pass

    @classmethod
    def start(cls, name, data, op):
        schema = Schema.query.filter(Schema.name == name).first()
        start = State.query.filter(State.catalog == State.S).filter(State.schema_id == schema.id).first()
        if cls.validate(start, data):
            workflow = Workflow(schema=schema, current=start, timestamp=int(datetime.datetime.now().timestamp() * 1000))
            data = Data(data=json.dumps(data), op=op, workflow=workflow, state=start, timestamp=int(datetime.datetime.now().timestamp() * 1000))
            db.session.add(workflow)
            db.session.add(data)
            try:
                db.session.commit()
                # TODO publish message {"workflow": $workflow.id, "state": $state.id}
                return EngineService(workflow)
            except Exception as e:
                db.session.rollback()
                raise e

    def trans(self, transform, data, op):
        transforms = {x.id for x in self.workflow.current.transforms}
        if transform.id not in transforms:
            raise Exception()
        state = transform.state
        if not self.validate(state, data):
            raise Exception()
        # TODO validate assigner
        workflow = Workflow(schema=self.workflow.schema, current=state, timestamp=int(datetime.datetime.now().timestamp() * 1000))
        data = Data(data=json.dumps(data), op=op, workflow=workflow, state=state, timestamp=int(datetime.datetime.now().timestamp() * 1000))
        db.session.add(workflow)
        db.session.add(data)
        try:
            db.session.commit()
            # TODO publish message
        except Exception as e:
            db.session.rollback()
            raise e