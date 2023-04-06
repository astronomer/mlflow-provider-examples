-- Table: public.predictions

-- DROP TABLE IF EXISTS public.predictions;

CREATE TABLE IF NOT EXISTS public.predictions
(
    feature_id integer NOT NULL,
    prediction smallint NOT NULL,
    CONSTRAINT feature_id FOREIGN KEY (feature_id)
        REFERENCES public.new_features (feature_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.predictions
    OWNER to postgres;
-- Index: fki_feature_id

-- DROP INDEX IF EXISTS public.fki_feature_id;

CREATE INDEX IF NOT EXISTS fki_feature_id
    ON public.predictions USING btree
    (feature_id ASC NULLS LAST)
    TABLESPACE pg_default;
