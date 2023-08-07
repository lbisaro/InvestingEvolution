CREATE TABLE `bot` (
  `idbot` int(12) NOT NULL,
  `idestrategia` int(10) NOT NULL,
  `prm_values` longtext NOT NULL,
  `idinterval` varchar(5) NOT NULL,
  `base_asset` varchar(12) NOT NULL,
  `quote_asset` varchar(12) NOT NULL,
  `quote_qty` decimal(18,8) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Volcado de datos para la tabla `bot`
--

INSERT INTO `bot` (`idbot`, `idestrategia`, `prm_values`, `idinterval`, `base_asset`, `quote_asset`, `quote_qty`) VALUES
(1, 1, '14,50,10', '0m01', 'BTC', 'USDT', '1000.00000000');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `bot_order`
--

CREATE TABLE `bot_order` (
  `idbotorder` int(12) NOT NULL,
  `idbot` int(11) NOT NULL,
  `datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `base_asset` varchar(14) NOT NULL,
  `quote_asset` varchar(14) NOT NULL,
  `side` tinyint(1) NOT NULL,
  `completed` tinyint(1) NOT NULL DEFAULT 0,
  `origQty` decimal(15,8) NOT NULL,
  `price` decimal(15,8) NOT NULL,
  `orderId` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `estrategia`
--

CREATE TABLE `estrategia` (
  `idestrategia` int(10) NOT NULL,
  `nom_estrategia` varchar(40) NOT NULL,
  `prm_name` longtext NOT NULL,
  `prm_default` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Volcado de datos para la tabla `estrategia`
--

INSERT INTO `estrategia` (`idestrategia`, `nom_estrategia`, `prm_name`, `prm_default`) VALUES
(1, 'ADX Alternancia', 'ADX Long Media Value,Velas previas,Porcentaje de capital por compra', '14,50,10');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `klines_1m`
--

CREATE TABLE `klines_1m` (
  `symbol` varchar(12) NOT NULL,
  `datetime` datetime NOT NULL,
  `open` decimal(15,8) NOT NULL,
  `close` decimal(15,8) NOT NULL,
  `high` decimal(15,8) NOT NULL,
  `low` decimal(15,8) NOT NULL,
  `volume` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `bot`
--
ALTER TABLE `bot`
  ADD PRIMARY KEY (`idbot`),
  ADD KEY `idestrategia` (`idestrategia`),
  ADD KEY `idinterval` (`idinterval`);

--
-- Indices de la tabla `bot_order`
--
ALTER TABLE `bot_order`
  ADD PRIMARY KEY (`idbotorder`),
  ADD KEY `idbot` (`idbot`) USING BTREE;

--
-- Indices de la tabla `estrategia`
--
ALTER TABLE `estrategia`
  ADD PRIMARY KEY (`idestrategia`);

--
-- Indices de la tabla `klines_1m`
--
ALTER TABLE `klines_1m`
  ADD UNIQUE KEY `symbol_2` (`symbol`,`datetime`),
  ADD KEY `datetime` (`datetime`),
  ADD KEY `symbol` (`symbol`) USING BTREE;

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `bot_order`
--
ALTER TABLE `bot_order`
  MODIFY `idbotorder` int(12) NOT NULL AUTO_INCREMENT;