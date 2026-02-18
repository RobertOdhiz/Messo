"""Initial: dlr_receipts and sent_sms tables

Revision ID: 001
Revises:
Create Date: 2025-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dlr_receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("received_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("body_json", sa.Text(), nullable=True),
        sa.Column("raw_body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(64), nullable=True),
        sa.Column("msisdn", sa.String(32), nullable=True),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sent_sms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("recipient", sa.String(32), nullable=False),
        sa.Column("message_preview", sa.String(256), nullable=True),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("success", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sent_sms")
    op.drop_table("dlr_receipts")
