CREATE TABLE `bot_order` (
  `idbotorder` int(12) NOT NULL,
  `idbot` int(11) NOT NULL,
  `datetime` datetime NOT NULL,
  `base_asset` varchar(14) NOT NULL,
  `quote_asset` varchar(14) NOT NULL,
  `side` tinyint(4) NOT NULL,
  `completed` tinyint(4) NOT NULL,
  `origQty` decimal(15,8) NOT NULL,
  `price` decimal(15,8) NOT NULL,
  `orderId` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `bot_order`
--
ALTER TABLE `bot_order`
  ADD PRIMARY KEY (`idbotorder`),
  ADD KEY `idbot` (`idbot`) USING BTREE;