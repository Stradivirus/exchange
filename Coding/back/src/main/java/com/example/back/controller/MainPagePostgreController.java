package com.example.back.controller;

import com.example.back.dto.exchange.ExchangeDto;
import com.example.back.dto.commodities.CommoditiesDto;
import com.example.back.dto.commodities_index.CommoditiesIndexDto;
import com.example.back.dto.grains.GrainsDto;
import com.example.back.dto.stock.StockDto;
import com.example.back.service.MainPagePostgreService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/postgre")
public class MainPagePostgreController {
    private final MainPagePostgreService mainPagePostgreService;

    // 최근 30개 전체 환율 데이터 조회
    @GetMapping("/exchange/latest30")
    public List<ExchangeDto> getLatest30Exchange() {
        return mainPagePostgreService.getLatest30Exchange();
    }

    // 곡물 전체(옥수수, 밀, 쌀, 커피, 설탕) 최신 30개를 한 번에 반환
    @GetMapping("/grains/latest30")
    public List<GrainsDto> getLatest30Grains() {
        return mainPagePostgreService.getLatest30GrainsDto();
    }

    // 원자재 전체(금, 은, 구리, 유가 등) 최신 30개를 한 번에 반환
    @GetMapping("/commodities/latest30")
    public List<CommoditiesDto> getLatest30Commodities() {
        return mainPagePostgreService.getLatest30CommoditiesDto();
    }

    // 지수 전체(DXY, VIX 등) 최신 30개를 한 번에 반환
    @GetMapping("/commodities_index/latest30")
    public List<CommoditiesIndexDto> getLatest30CommoditiesIndex() {
        return mainPagePostgreService.getLatest30CommoditiesIndexDto();
    }

    // 주식 전체(SP500, DOW JONES, NASDAQ, KOSPI, KOSDAQ) 최신 30개를 한 번에 반환
    @GetMapping("/stock/latest30")
    public List<StockDto> getLatest30Stock() {
        return mainPagePostgreService.getLatest30StockDto();
    }
}