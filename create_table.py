#!/usr/bin/env python3
from app.data.db import engine
from sqlalchemy import text


def create_attendance_evidences_table():
    try:
        with engine.connect() as conn:
            # Create enum type safely
            conn.execute(
                text(
                    """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'evidence_type_enum') THEN
                        CREATE TYPE evidence_type_enum AS ENUM ('check_in', 'check_out');
                    END IF;
                END
                $$;
            """
                )
            )

            # Create table
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS attendance_evidences (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                    evidence_type evidence_type_enum NOT NULL,
                    image_bucket VARCHAR(128) NOT NULL,
                    image_path VARCHAR NOT NULL,
                    image_mime VARCHAR(64),
                    image_size INTEGER,
                    verified BOOLEAN NOT NULL DEFAULT FALSE,
                    confidence_score FLOAT,
                    verification_notes VARCHAR,
                    verified_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """
                )
            )

            # Create indexes
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS ix_evidence_session_type ON attendance_evidences (session_id, evidence_type);
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS ix_evidence_verified ON attendance_evidences (verified);
            """
                )
            )

            conn.commit()
            print("✅ attendance_evidences table created successfully!")

    except Exception as e:
        print(f"❌ Error creating table: {e}")
        raise


if __name__ == "__main__":
    create_attendance_evidences_table()
