package com.example.back.repository;
import java.time.LocalDate;

import com.example.back.entity.DailyExchange;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DailyExchangeRepository extends JpaRepository<DailyExchange, LocalDate> {
    // 추가 쿼리 메서드는 필요시 작성
}
