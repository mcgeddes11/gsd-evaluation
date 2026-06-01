from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'])
    )
    op.create_index(op.f('ix_media_filename'), 'media', ['filename'], unique=True)
    op.create_index(op.f('ix_media_file_path'), 'media', ['file_path'], unique=True)
    op.create_index(op.f('ix_media_uploader_id'), 'media', ['uploader_id'])


def downgrade():
    op.drop_index(op.f('ix_media_uploader_id'), table_name='media')
    op.drop_index(op.f('ix_media_file_path'), table_name='media')
    op.drop_index(op.f('ix_media_filename'), table_name='media')
    op.drop_table('media')

