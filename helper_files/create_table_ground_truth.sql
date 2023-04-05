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
