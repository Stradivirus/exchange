package com.example.back.repository.exchange;

import com.example.back.entity.exchange.Exchange;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface ExchangeRepository extends JpaRepository<Exchange, LocalDate> {
    List<Exchange> findTop30ByOrderByDateDesc();
}