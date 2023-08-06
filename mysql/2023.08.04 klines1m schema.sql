CREATE TABLE `klines_1m` (
  `symbol` varchar(12) NOT NULL,
  `datetime` datetime NOT NULL,
  `open` decimal(15,8) NOT NULL,
  `close` decimal(15,8) NOT NULL,
  `high` decimal(15,8) NOT NULL,
  `low` decimal(15,8) NOT NULL,
  `volume` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `klines_1m`
--
ALTER TABLE `klines_1m`
  ADD UNIQUE KEY `symbol_2` (`symbol`,`datetime`),
  ADD KEY `datetime` (`datetime`),
  ADD KEY `symbol` (`symbol`) USING BTREE;
