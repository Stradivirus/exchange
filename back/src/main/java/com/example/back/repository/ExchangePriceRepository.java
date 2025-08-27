package com.example.back.repository;

import com.example.back.entity.ExchangePrice;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Date;
import java.util.List;

public interface ExchangePriceRepository extends MongoRepository<ExchangePrice, String> {
    // 날짜 기준으로 환율 데이터 조회
    List<ExchangePrice> findByDatetimeBetween(Date start, Date end);
}
