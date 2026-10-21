-- Card access tracking for members (public.induction).
-- Safe to run more than once.

BEGIN;

ALTER TABLE public.induction
    ADD COLUMN IF NOT EXISTS committee_cabinet BOOLEAN NOT NULL DEFAULT FALSE;

COMMIT;
