from sqlalchemy.orm import Session

from app.models.grammar import Grammar

from app.schemas.grammar import (
    GrammarCreate,
    GrammarUpdate,
)


class GrammarRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(Grammar)
            .order_by(
                Grammar.order_index,
            )
            .all()
        )

    def get(
        self,
        grammar_id: str,
    ):
        return (
            self.db.query(Grammar)
            .filter(
                Grammar.id == grammar_id,
            )
            .first()
        )

    def create(
        self,
        data: GrammarCreate,
    ):
        grammar = Grammar(
            **data.model_dump(),
        )

        self.db.add(grammar)
        self.db.commit()
        self.db.refresh(grammar)

        return grammar

    def update(
        self,
        grammar: Grammar,
        data: GrammarUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                grammar,
                key,
                value,
            )

        self.db.commit()
        self.db.refresh(grammar)

        return grammar

    def delete(
        self,
        grammar: Grammar,
    ):
        self.db.delete(grammar)
        self.db.commit()