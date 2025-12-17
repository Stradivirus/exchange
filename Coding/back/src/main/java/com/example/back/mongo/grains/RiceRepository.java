package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List; // 필수 추가

public interface RiceRepository extends MongoRepository<Rice, String> {
    Rice findTopByOrderByDateDesc();

    List<Rice> findTop30ByOrderByDateDesc();
}
