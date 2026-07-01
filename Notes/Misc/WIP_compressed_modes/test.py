from bin_tools  import Encoder,Decoder
from bin_scenes import scene2bin,bin2scene

j = r"""
{
  "offsets": {
    "joe egg": 22,
    "weeeeeeeeeeeeeeweeeeeeeeeeeeee": 831272
  },
  "*": [
    {
      "1": [
        210,
        1,
        1,
        245,
        255
      ],
      "fx": [
        [
          1,
          6,
          0
        ]
      ]
    },
    {
      "*": [
        {
          "1": [
            45,
            0,
            5045887
          ],
          "fx": [
            [
              0
            ],
            [
              2,
              0.41960784
            ]
          ]
        },
        {
          "1": [
            45,
            2,
            0.28736112,
            0.61,
            13122451,
            5692738,
            13831218,
            3333682
          ],
          "fx": [
            [
              2,
              1
            ]
          ]
        }
      ],
      "fx": [
        [
          1,
          28.8,
          -43
        ],
        [
          2,
          0.31764704
        ]
      ]
    }
  ],
  "fx": [
    [
      1,
      -2.2,
      0
    ],
    [
      2,
      1
    ]
  ]
}
"""

from json import loads
x = loads(j)       ; print(x)

𝔈 = Encoder()
x = scene2bin(𝔈,x) ; print(𝔈)
print(𝔈.B)
𝔇 = Decoder(𝔈)
x = bin2scene(𝔇)   ; print(x)

# 𝔈 = Encoder()
x = scene2bin(𝔈,x) ; print(𝔈)
𝔇 = Decoder(𝔈)
x = bin2scene(𝔇)   ; print(x)
x = bin2scene(𝔇)   ; print(x)

# def round(x,p=0):
#   x = scene2bin(x)
#   if p: print(x)
#   x = bin2scene(Reader(x))
#   if p: print(x)
#   return x

# from json import loads
# x = loads(j)
# print(x)
# α = round(x,1)
# for i in range(10): x=round(x)
# β = round(x,1)
# print(α==β)