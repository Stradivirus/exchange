package com.example.back.service;
// (불필요한 import 제거)
import com.example.back.entity.exchange.Exchange;
import com.example.back.repository.exchange.ExchangeRepository;
import com.example.back.entity.commodities.Commodities;
import com.example.back.repository.commodities.CommoditiesRepository;
import com.example.back.entity.commodities_index.CommoditiesIndex;
import com.example.back.repository.commodities_index.CommoditiesIndexRepository;
import com.example.back.entity.grains.Grains;
import com.example.back.repository.grains.GrainsRepository;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import com.example.back.repository.stock.StockRepository;
import com.example.back.dto.stock.StockDto;

import java.util.List;
import java.util.stream.Collectors;
import com.example.back.dto.commodities.CommoditiesDto;
import com.example.back.dto.commodities_index.DxyDto;
import com.example.back.dto.commodities_index.VixDto;
import com.example.back.dto.commodities_index.CommoditiesIndexDto;
import com.example.back.dto.grains.GrainsDto;

import com.example.back.dto.exchange.ExchangeDto;


@Service
@RequiredArgsConstructor
public class MainPagePostgreService {
    private final ExchangeRepository exchangeRepository;
    private final CommoditiesRepository commoditiesRepository;
    private final CommoditiesIndexRepository commoditiesIndexRepository;
    private final GrainsRepository grainsRepository;
    private final StockRepository stockRepository;
    // 최근 30개 주식 데이터를 StockDto로 변환하여 반환
    public List<StockDto> getLatest30StockDto() {
        return stockRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> StockDto.builder()
                .date(e.getDate())
                .sp500(e.getSp500())
                .sp500Volume(e.getSp500Volume())
                .dowJones(e.getDowJones())
                .dowJonesVolume(e.getDowJonesVolume())
                .nasdaq(e.getNasdaq())
                .nasdaqVolume(e.getNasdaqVolume())
                .kospi(e.getKospi())
                .kospiVolume(e.getKospiVolume())
                .kosdaq(e.getKosdaq())
                .kosdaqVolume(e.getKosdaqVolume())
                .build())
            .collect(Collectors.toList());
    }

    // DXY 최신 30개
    public List<DxyDto> getLatest30Dxy() {
        return commoditiesIndexRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> DxyDto.builder()
                .date(java.sql.Date.valueOf(e.getDate()))
                .price(e.getDxy())
                .build())
            .collect(Collectors.toList());
    }

    // VIX 최신 30개
    public List<VixDto> getLatest30Vix() {
        return commoditiesIndexRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> VixDto.builder()
                .date(java.sql.Date.valueOf(e.getDate()))
                .price(e.getVix())
                .build())
            .collect(Collectors.toList());
    }

    // 최근 30개 전체 환율 데이터 조회
    public List<ExchangeDto> getLatest30Exchange() {
        List<Exchange> exchangeList = exchangeRepository.findTop30ByOrderByDateDesc();
        return exchangeList.stream()
                .map(e -> ExchangeDto.builder()
                        .date(e.getDate())
                        .usd(e.getUsd())
                        .jpy(e.getJpy())
                        .eur(e.getEur())
                        .cny(e.getCny())
                        .build())
                .collect(Collectors.toList());
    }

    // 최근 30개 원자재 데이터 조회
    public List<Commodities> getLatest30Commodities() {
        return commoditiesRepository.findTop30ByOrderByDateDesc();
    }

    // 최근 30개 원자재 데이터를 CommoditiesDto로 변환하여 반환
    public List<CommoditiesDto> getLatest30CommoditiesDto() {
        return commoditiesRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> CommoditiesDto.builder()
                .date(java.sql.Date.valueOf(e.getDate()))
                .gold(e.getGold())
                .goldVolume(e.getGoldVolume())
                .silver(e.getSilver())
                .silverVolume(e.getSilverVolume())
                .copper(e.getCopper())
                .copperVolume(e.getCopperVolume())
                .crudeOil(e.getCrudeOil())
                .crudeOilVolume(e.getCrudeOilVolume())
                .brentOil(e.getBrentOil())
                .brentOilVolume(e.getBrentOilVolume())
                .build())
            .collect(java.util.stream.Collectors.toList());
    }

    // 최근 30개 지수 데이터 조회
    public List<CommoditiesIndex> getLatest30CommoditiesIndex() {
        return commoditiesIndexRepository.findTop30ByOrderByDateDesc();
    }

    // 최근 30개 지수 데이터를 CommoditiesIndexDto로 변환하여 반환
    public List<CommoditiesIndexDto> getLatest30CommoditiesIndexDto() {
        return commoditiesIndexRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> CommoditiesIndexDto.builder()
                .date(java.sql.Date.valueOf(e.getDate()))
                .dxy(e.getDxy())
                .vix(e.getVix())
                .build())
            .collect(java.util.stream.Collectors.toList());
    }

    // 최근 30개 곡물 데이터 조회
    public List<Grains> getLatest30Grains() {
        return grainsRepository.findTop30ByOrderByDateDesc();
    }

    // 최근 30개 곡물 데이터를 GrainsDto로 변환하여 반환
    public List<GrainsDto> getLatest30GrainsDto() {
        return grainsRepository.findTop30ByOrderByDateDesc().stream()
            .map(e -> GrainsDto.builder()
                .date(java.sql.Date.valueOf(e.getDate()))
                .corn(e.getCorn())
                .cornVolume(e.getCornVolume())
                .wheat(e.getWheat())
                .wheatVolume(e.getWheatVolume())
                .rice(e.getRice())
                .riceVolume(e.getRiceVolume())
                .coffee(e.getCoffee())
                .coffeeVolume(e.getCoffeeVolume())
                .sugar(e.getSugar())
                .sugarVolume(e.getSugarVolume())
                .build())
            .collect(java.util.stream.Collectors.toList());
    }
}