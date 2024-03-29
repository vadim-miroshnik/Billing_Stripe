"""upd payment

Revision ID: f2a5ed96ac71
Revises: 954071a37f53
Create Date: 2023-03-17 00:31:06.711421

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a5ed96ac71"
down_revision = "954071a37f53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('alembic_version')
    op.add_column("payment", sa.Column("payment_intent_id", sa.String(), nullable=True))
    op.alter_column("payment", "description", existing_type=sa.VARCHAR(), nullable=True)
    op.drop_constraint("payment_description_key", "payment", type_="unique")
    op.create_unique_constraint(None, "payment", ["id"], schema="users")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "payment", schema="users", type_="unique")
    op.create_unique_constraint("payment_description_key", "payment", ["description"])
    op.alter_column("payment", "description", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("payment", "payment_intent_id")
    op.create_table(
        "alembic_version",
        sa.Column("version_num", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("version_num", name="alembic_version_pkc"),
    )
    # ### end Alembic commands ###
