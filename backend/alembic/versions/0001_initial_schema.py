"""initial schema: users, favorites and watch_later

Squashes the eight migrations of the interview-era database into the one shape
the application actually ships.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _saved_list(table_name: str) -> None:
    """Create one of the two saved lists — they hold exactly the same columns."""
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("poster_path", sa.String(), nullable=True),
        sa.Column("imdb_id", sa.String(), nullable=True),
        sa.Column("imdb_rating", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=f"fk_{table_name}_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "tmdb_id", name=f"uq_{table_name}_user_movie"),
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column(
            "user_created_at",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    # users first: both lists carry a foreign key to it, and Postgres refuses a
    # reference to a table that does not exist yet.
    _saved_list("favorites")
    _saved_list("watch_later")


def downgrade() -> None:
    op.drop_table("watch_later")
    op.drop_table("favorites")
    op.drop_table("users")
