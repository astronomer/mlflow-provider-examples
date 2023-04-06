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
