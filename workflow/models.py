from m.extensions.sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, BLOB
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


db = SQLAlchemy(config_prefix='database')


class Schema(db.Model):
    __tablename__ = 'schema'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), unique=True, nullable=False)
    editable = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=False)


class State(db.Model):
    __tablename__ = 'state'
    __table_args__ = (UniqueConstraint('schema_id', 'name', name='unique_state_name'))
    M = 0
    S = 1
    E = 2

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_id = Column(Integer, ForeignKey('schema.id'), nullable=False)
    name = Column(String(45), nullable=False)
    catalog = Column(Integer, nullable=False, default=M)

    schema = relationship('Schema')
    fields = relationship('Field')
    ops = relationship('Op')
    transforms = relationship('Transform', back_populates='state', foreign_keys='[Transform.perv]')


class Field(db.Model):
    __tablename__ = 'field'
    __table_args__ = (UniqueConstraint('state_id', 'name', name='unique_state_field'))

    INT = 0
    FLOAT = 1
    STRING = 2
    DATETIME = 3

    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(Integer, ForeignKey('state.id'), nullable=False)
    name = Column(String(45), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    type = Column(Integer, nullable=False, default=STRING)
    desc = Column(String(1024), nullable=True)


class Op(db.Model):
    __tablename__ = 'op'

    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(Integer, ForeignKey('state.id'), nullable=False)
    name = Column(String(45), nullable=False)


class Transform(db.Model):
    __tablename__ = 'transform'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    prev = Column(Integer, ForeignKey('state.id'), nullable=False)
    next = Column(Integer, ForeignKey('state.id'), nullable=False)

    state = relationship('State', back_populates='transforms', foreign_keys=[next])


class Workflow(db.Model):
    __tablename__ = 'workflow'

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_id = Column(Integer, ForeignKey('schema.id'), nullable=False)
    state_id = Column(Integer, ForeignKey('state.id'), nullable=False)
    timestamp = Column(Integer, nullable=False)
    assigner = Column(String(45), nullable=True, index=True)

    schema = relationship('Schema')
    current = relationship('State')


class Data(db.Model):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    state_id = Column(Integer, ForeignKey('state.id'), nullable=False)
    timestamp = Column(Integer, nullable=False)
    data = Column(BLOB, nullable=True)
    op = Column(String(45), nullable=False)

    workflow = relationship('Workflow')
    state = relationship('State')