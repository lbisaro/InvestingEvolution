SELECT concat(base_asset,quote_asset) as symbol, 
       sum( if( (side = 1), (price * qty) ,((price * qty) -1) ) ) AS usdt,
       sum( if( (side = 0), (1) ,(0) ) ) AS compras,
       sum( if( (side = 1), (1) ,(0) ) ) AS ventas
  FROM bot_order 
  GROUP BY base_asset,quote_asset