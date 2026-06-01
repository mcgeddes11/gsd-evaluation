from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('avatar_filename', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('users', 'avatar_filename')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')