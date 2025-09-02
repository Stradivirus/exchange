package com.example.back.service;

import com.example.back.entity.DailyExchange;
import com.example.back.repository.DailyExchangeRepository;
import com.example.back.dto.DailyExchangeResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class DailyExchangeService {
    private final DailyExchangeRepository dailyExchangeRepository;

    public DailyExchangeResponse getLatestDailyExchange() {
        Optional<DailyExchange> latest = dailyExchangeRepository.findAll()
                .stream()
                .max((a, b) -> a.getDate().compareTo(b.getDate()));
        return latest.map(this::toResponse).orElse(null);
    }

    public DailyExchangeResponse getDailyExchangeByDate(LocalDate date) {
        return dailyExchangeRepository.findById(date)
                .map(this::toResponse)
                .orElse(null);
    }

    private DailyExchangeResponse toResponse(DailyExchange entity) {
        return DailyExchangeResponse.builder()
                .date(entity.getDate())
                .dollar(entity.getDollar())
                .gold(entity.getGold())
                .oil(entity.getOil())
                .dxy(entity.getDxy())
                .baseRate(entity.getBaseRate())
                .usBaseRate(entity.getUsBaseRate())
                .build();
    }
}
