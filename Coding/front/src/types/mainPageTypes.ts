// src/types/mainPageTypes.ts

export interface CommoditiesDto {
  date: string;
  gold: number;
  silver: number;
  copper: number;
  crudeOil: number;
  brentOil: number;
}
export interface CommoditiesIndexDto {
  date: string;
  dxy: number;
  vix: number;
}
export interface ExchangeDto {
  date: string;
  usd: number;
  jpy: number;
  eur: number;
  cny: number;
}
export interface InterestRateDto {
  date: string;
  korBaseRate: number;
  usFedRate: number;
}
export interface StockDto {
  date: string;
  sp500: number;
  dowJones: number;
  nasdaq: number;
  kospi: number;
  kosdaq: number;
}
export interface MainPageResponseDto {
  commodities: CommoditiesDto | null;
  commoditiesIndex: CommoditiesIndexDto | null;
  exchange: ExchangeDto | null;
  interestRate: InterestRateDto | null;
  stock: StockDto | null;
}
