package com.example.back.controller;

import com.example.back.service.MainPageMongoService;
import com.example.back.dto.MainPageResponseDto;
import com.example.back.dto.commodities.CommoditiesDto;
import com.example.back.dto.commodities_index.CommoditiesIndexDto;
import com.example.back.dto.exchange.ExchangeDto;
import com.example.back.dto.grains.GrainsDto;
import com.example.back.dto.stock.StockDto;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/mongo") // 프론트엔드 요청 경로 확인 필요 (기존 postgre 경로를 대체하려면 변경 고려)
public class MainPageMongoController {
    private final MainPageMongoService mainPageMongoService;

    // 기존: 메인 페이지용 최신 데이터 1건 (변경 없음)
    @GetMapping("/latest")
    public MainPageResponseDto getLatestMainPageInfo() {
        return mainPageMongoService.getLatestMainPageInfo();
    }

    // [추가] 환율 30개 조회
    @GetMapping("/exchange/latest30")
    public List<ExchangeDto> getLatest30Exchange() {
        return mainPageMongoService.getLatest30Exchange();
    }

    // [추가] 곡물 30개 조회
    @GetMapping("/grains/latest30")
    public List<GrainsDto> getLatest30Grains() {
        return mainPageMongoService.getLatest30GrainsDto();
    }

    // [추가] 원자재 30개 조회
    @GetMapping("/commodities/latest30")
    public List<CommoditiesDto> getLatest30Commodities() {
        return mainPageMongoService.getLatest30CommoditiesDto();
    }

    // [추가] 지수 30개 조회
    @GetMapping("/commodities_index/latest30")
    public List<CommoditiesIndexDto> getLatest30CommoditiesIndex() {
        return mainPageMongoService.getLatest30CommoditiesIndexDto();
    }

    // [추가] 주식 30개 조회
    @GetMapping("/stock/latest30")
    public List<StockDto> getLatest30Stock() {
        return mainPageMongoService.getLatest30StockDto();
    }
}