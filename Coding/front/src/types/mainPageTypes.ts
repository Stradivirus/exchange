// src/types/mainPageTypes.ts


// 상세 DTO 예시 (실제 백엔드 구조에 맞게 확장 가능)
export interface GoldDto {
  date: string;
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  price: number;
}

export interface CommoditiesIndexDto {
  date: string;
  close: number;
  open: number;
  high: number;
  low: number;
}

export interface ExchangeDto {
  date: string;
  rate: number;
  unit_name: string;
}

export interface InterestRateDto {
  date: string;
  rate: number;
}

export interface StockDto {
  date: string;
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
}

export interface MainPageResponseDto {
  // grains
  riceList: any[];
  wheatList: any[];
  cornList: any[];
  coffeeList: any[];
  sugarList: any[];
  // commodities
  goldList: GoldDto[];
  silverList: any[];
  copperList: any[];
  crudeOilList: any[];
  brentOilList: any[];
  // commodities index
  dxyList: CommoditiesIndexDto[];
  vixList: CommoditiesIndexDto[];
  // exchange
  usdList: ExchangeDto[];
  jpyList: ExchangeDto[];
  eurList: ExchangeDto[];
  cnyList: ExchangeDto[];
  // interest
  korBaseRateList: InterestRateDto[];
  usFedRateList: InterestRateDto[];
  // stock
  sp500List: StockDto[];
  dowJonesList: StockDto[];
  nasdaqList: StockDto[];
  kospiList: StockDto[];
  kosdaqList: StockDto[];
}
