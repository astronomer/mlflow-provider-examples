-- Table: public.iris_ground_truth

-- DROP TABLE IF EXISTS public.iris_ground_truth;

CREATE TABLE IF NOT EXISTS public.iris_ground_truth
(
    feature_id integer NOT NULL,
    sepal_length_cm double precision NOT NULL,
    sepal_width_cm double precision NOT NULL,
    petal_length_cm double precision NOT NULL,
    petal_width_cm double precision NOT NULL,
    target smallint NOT NULL,
    CONSTRAINT iris_ground_truth_pkey PRIMARY KEY (feature_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.iris_ground_truth
    OWNER to postgres;


-- SEQUENCE: public.new_features_feature_id_seq

-- DROP SEQUENCE IF EXISTS public.new_features_feature_id_seq;

CREATE SEQUENCE IF NOT EXISTS public.new_features_feature_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.new_features_feature_id_seq
    OWNER TO postgres;


-- Table: public.new_features

-- DROP TABLE IF EXISTS public.new_features;

CREATE TABLE IF NOT EXISTS public.new_features
(
    feature_id integer NOT NULL DEFAULT nextval('new_features_feature_id_seq'::regclass),
    sepal_length_cm double precision,
    sepal_width_cm double precision,
    petal_length_cm double precision,
    petal_width_cm double precision,
    created_at timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT new_features_pkey PRIMARY KEY (feature_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.new_features
    OWNER to postgres;


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

-- Table: public.true_values

-- DROP TABLE IF EXISTS public.true_values;

CREATE TABLE IF NOT EXISTS public.true_values
(
    feature_id bigint,
    true_values bigint
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.true_values
    OWNER to postgres;

